# app/forms/__init__.py
"""
WTForms package
"""

from .auth import LoginForm
from .admin import CreateUserForm, UpdateUserForm, ChangePasswordForm, BulkUserActionForm
from .research import ResearchBriefForm, EditBriefForm

__all__ = ['LoginForm', 'CreateUserForm', 'UpdateUserForm', 'ChangePasswordForm', 'BulkUserActionForm', 
           'ResearchBriefForm', 'EditBriefForm']
