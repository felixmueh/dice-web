from dice import FiniteMeasure, dice_interpreter, dicefunction


def build_result():
    session = dice_interpreter()

    @dicefunction
    def weather():
        return FiniteMeasure((("sun", 2), ("rain", 1)))

    session.register_function(weather)
    return session("d weather()")
