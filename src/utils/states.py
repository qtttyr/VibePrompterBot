from aiogram.fsm.state import State, StatesGroup


class PromptGen(StatesGroup):
    project_info = State()
    editor = State()
    stack = State()
    model = State()
    idea = State()


class FolderGen(StatesGroup):
    project_pick = State()   # user types a new project description
    scope = State()          # user picks backend / frontend / fullstack
