import logging
import json
from math import floor
from pymongo import MongoClient
from tornado.gen import coroutine
from tornado.web import RequestHandler, HTTPError, MissingArgumentError


class RewardsBaseHandler(RequestHandler):

    def initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        # self.logger.info("MSG=Configured logging")

    def prepare(self):
        self.client = MongoClient("mongodb", 27017)
        self.db = self.client["Rewards"]
        self.logger.info("HOST=mongodb, PORT=27017, DB=Rewards, MSG=Opened Connection")

    def on_finish(self):
        self.client.close()
        self.logger.info("HOST=mongodb, PORT=27017, DB=Rewards, MSG=Closed connection")


class RewardsHandler(RewardsBaseHandler):
    
    @coroutine
    def get(self):
        rewards = list(self.db.rewards.find({}, {"_id": 0}))
        self.write(json.dumps(rewards))


class CustomerRewardsHandler(RewardsBaseHandler):

    def _get_tier(self, points):
        if self.db.rewards.find({"points":{"$lte":points}}).count() == 0:
            self.logger.info("MSG=Identified that the user is not yet in a tier, POINTS={}".format(points))
            return None
        tier = list(self.db.rewards.find({"points":{"$lte":points}}).sort([("points", -1)]).limit(1))[0]
        self.logger.info("MSG=Identified current tier, TIER={}, POINTS={}".format(tier["tier"], points))
        return tier


    def _get_next_tier(self, points):
        if self.db.rewards.find({"points":{"$gt":points}}).count() == 0:
            self.logger.info("MSG=Identified that the user is already in the top tier, POINTS={}".format(points))
            return None
        next_tier = list(self.db.rewards.find({"points":{"$gt":points}}).sort([("points", 1)]).limit(1))[0]
        self.logger.info("MSG=Identified next tier, TIER={}, POINTS={}".format(next_tier["tier"], points))
        return next_tier


    def prepare(self):
        super(CustomerRewardsHandler, self).prepare()
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            if type(self.request.body) != str:
                self.json_args = json.loads(self.request.body.decode("utf-8"))
            else:
                self.json_args = json.loads(self.request.body)
            self.logger.info("MSG=Parsed JSON, INPUT={}".format(str(self.json_args)))
        else:
            self.json_args = None

    @coroutine
    def put(self):
        email = self.json_args.get("email")
        if not email:
            raise MissingArgumentError("email")
        order_total = self.json_args.get("order_total")
        if not order_total:
            raise MissingArgumentError("order_total")
        # TODO: What if someone hands us a negative value?  Should we be in the business of refunding points?
        try:
            order_total = float(order_total)
        except ValueError:
            raise HTTPError(status=417, reason="Order variable provided is not a float")
        self.logger.info("MSG=Parsed arguments, EMAIL={}, ORDER={}".format(email, order_total))
        current_customer_exists = self.db.customer_rewards.find_one({"email_address":email}, {"_id":0})
        if current_customer_exists:
            updated_document = current_customer_exists
            self.logger.info("MSG=Identified existing customer, EMAIL={}, POINTS={}".format(email, updated_document["rewards_points"]))
            updated_document["rewards_points"] += floor(order_total)
        else:
            self.logger.info("MSG=Identified no existing customer, EMAIL={}".format(email))
            updated_document = {
                "email_address":email,
                "rewards_points": floor(order_total)
            }
        tier = self._get_tier(updated_document["rewards_points"])
        if tier:
            updated_document["rewards_tier"] = tier["tier"]
            updated_document["rewards_tier_name"] = tier["rewardName"]
        # Handle case where use had not yet reached a tier
        else:
            updated_document["rewards_tier"] = None
            updated_document["rewards_tier_name"] = None
        next_tier = self._get_next_tier(updated_document["rewards_points"])
        if next_tier:
            updated_document["next_rewards_tier"] = next_tier["tier"]
            updated_document["next_rewards_tier_name"] = next_tier["rewardName"]
            points_to_next_tier = next_tier["points"] - tier["points"]
            points_gathered = updated_document["rewards_points"] - tier["points"]
            self.logger.info("MSG=Identified point progress, CURRENT={}, INCREMENT={}".format(points_gathered, points_to_next_tier))
            updated_document["next_rewards_tier_progress"] = round(points_gathered/points_to_next_tier, 2)
        # Handle case where user is at the maximum teir
        else:
            updated_document["next_rewards_tier"] = None
            updated_document["next_rewards_tier_name"] = None
            updated_document["next_rewards_tier_progress"] = 0
        result = self.db.customer_rewards.update_one({"email_address":email}, {"$set":updated_document}, True)
        # result.modified_count, result.match_count
        self.write(json.dumps(updated_document))
