"""Permission service for user authorization classification."""

from __future__ import annotations

import logging

from pnetai_chatbot.domain.enums.user_permission import UserPermission

logger = logging.getLogger(__name__)


class PermissionService:
    """Service to evaluate permission scopes for guests and authenticated users."""

    @staticmethod
    def get_user_permission(is_authenticated: bool) -> UserPermission:
        """Get the UserPermission classification.

        Args:
            is_authenticated: Whether the user is authenticated.

        Returns:
            The UserPermission enum value.
        """
        if is_authenticated:
            return UserPermission.MEMBER
        return UserPermission.GUEST

    def can_access_orders(self, is_authenticated: bool) -> bool:
        """Check if user can access the orders collection.

        Args:
            is_authenticated: Whether the user is authenticated.

        Returns:
            True if access is permitted, False otherwise.
        """
        permission = self.get_user_permission(is_authenticated)
        return permission != UserPermission.GUEST
