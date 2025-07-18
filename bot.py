import os # أضف هذا السطر
import logging
import asyncio
import random
import string
import httpx

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# اقرأ التوكن من متغيرات البيئة بدلاً من كتابته مباشرة
TOKEN = os.environ.get('TOKEN')

# ... باقي الكود يبقى كما هو ...
