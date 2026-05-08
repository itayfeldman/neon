from collections import namedtuple

Position = namedtuple(
    "Position",
    [
        "account_id",
        "asset_id",
        "quantity",
        "cost_basis",
        "current_price",
        "current_value",
        "unrealized_gain_loss",
        "unrealized_gain_loss_percent",
    ],
)
