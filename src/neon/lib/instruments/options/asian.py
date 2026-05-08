from neon.lib.instruments.options.base import BaseOption
from neon.lib.instruments.options.option_inputs import OptionInputs


class AsianOption(BaseOption):
    def __init__(self, inputs: OptionInputs):
        super().__init__(inputs)

    def price(self) -> float:
        raise NotImplementedError("American option pricing is not implemented yet.")
