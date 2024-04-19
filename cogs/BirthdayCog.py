import asyncio
import csv
import math
import random
import typing
import warnings
import io

import discord
import numpy as np
from discord import app_commands
from matplotlib import pyplot as plt

from src import utils, DataManager
from src.DefaultCog import DefaultCog


class BirthdayCog(DefaultCog):
    """
    handles the birthday (de)registration, calendar generation as well as automatic notifications for the bot
    """