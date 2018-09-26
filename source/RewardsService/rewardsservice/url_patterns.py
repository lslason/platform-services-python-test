from handlers.rewards_handler import RewardsHandler, CustomerRewardsHandler

url_patterns = [
    (r'/rewards', RewardsHandler),
    (r'/customer_rewards', CustomerRewardsHandler),
]
