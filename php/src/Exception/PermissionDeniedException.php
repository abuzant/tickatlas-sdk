<?php

declare(strict_types=1);

namespace TickAtlas\Exception;

/**
 * HTTP 403 — the key/account is blocked or the endpoint requires a higher plan
 * or scope (API_KEY_DISABLED, API_KEY_EXPIRED, IP_NOT_ALLOWED, ACCOUNT_*,
 * PERMISSION_DENIED, PLAN_UPGRADE_REQUIRED).
 */
class PermissionDeniedException extends ApiException
{
}
