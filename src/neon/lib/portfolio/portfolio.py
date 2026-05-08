from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Portfolio:
    name: str
    assets: dict = field(default_factory=dict)

    def add_asset(self, asset_name: str, quantity: float):
        if asset_name in self.assets:
            self.assets[asset_name] += quantity
        else:
            self.assets[asset_name] = quantity

    def remove_asset(self, asset_name: str, quantity: float):
        if asset_name in self.assets:
            if self.assets[asset_name] >= quantity:
                self.assets[asset_name] -= quantity
                if self.assets[asset_name] == 0:
                    del self.assets[asset_name]
            else:
                raise ValueError(f"Not enough quantity of {asset_name} to remove.")
        else:
            raise ValueError(f"Asset {asset_name} not found in portfolio.")

    def get_asset_quantity(self, asset_name: str) -> float:
        return self.assets.get(asset_name, 0.0)

    def get_total_assets(self) -> dict:
        return self.assets.copy()


# Example usage:
if __name__ == "__main__":
    portfolio = Portfolio("My Portfolio")
    portfolio.add_asset("AAPL", 10)
    portfolio.add_asset("GOOGL", 5)
    print(portfolio.get_total_assets())  # Output: {'AAPL': 10, 'GOOGL': 5}
    portfolio.remove_asset("AAPL", 5)
    print(portfolio.get_asset_quantity("AAPL"))  # Output: 5
