from aiogram.dispatcher.filters.state import State, StatesGroup


class GeneratingNewConfig(StatesGroup):
    waiting_for_config_name = State()


class AskSupport(StatesGroup):
    waiting_for_question = State()
