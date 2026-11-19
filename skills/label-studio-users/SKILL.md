---
name: label-studio-users
description: Add a Label Studio user with a password, reset a password, list users or make an invite link on a self-hosted Community instance. Use on "add an annotator", "give X a login", "reset the password", "invite link", "list users".
---

# Manage Label Studio users

Load settings first: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/overlay.py show` (see `setup`). Commands below use `lsctl` for `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/labelstudio.py`; it needs the token in the variable named by `LABEL_STUDIO_TOKEN_ENV` (inject it with the user's secrets tool; never write it to a file). Writes are dry runs until `--confirm`. Community edition has one organisation: every user sees every project. If a gateway sits in front of the instance,
the person must also be allowed through it (do that in the gateway's own tooling).

## Add a user with a password (Django shell route; the REST API can't reliably set passwords)

1. **Password:** generate it in the user's password manager; never put it in argv or a file. Read it into a variable.
2. **Create the account** by piping a script to the container's Django shell (container name and host from the overlay's
   `label-studio-users.md` if the user keeps one):
   ```python
   from users.models import User
   from organizations.models import Organization
   email = "<email>"
   org = Organization.objects.order_by("id").first()
   u, created = User.objects.get_or_create(email=email, defaults={"username": email, "first_name": "<Name>"})
   u.set_password(PW); u.active_organization = org; u.save()
   if not org.has_user(u): org.add_user(u)
   print("created" if created else "updated", u.id)
   ```
   Build the `PW = ...` line with Python `repr` so quotes are safe, and send it on stdin:
   `{ python3 -c 'import os; print("PW = %r" % os.environ["PW"])'; cat create_user.py; } | ssh <host> 'docker exec -i <container> python /label-studio/label_studio/manage.py shell'`.
   Re-running it resets the password.
3. **Verify:** GET `/user/login/` for the csrftoken, POST `email`, `password`, `csrfmiddlewaretoken` with a Referer header;
   expect 302 to `/`, then `/api/current-user/whoami` returns the user.
4. **Tell them:** the URL, how to log in, and what to label.

## Other jobs

- List: `GET /api/users` (a bare list).
- Invite link instead of a password: `GET /api/invite` returns a signup URL (signup without a link is disabled).
- Remove: `DELETE /api/organizations/<org>/memberships/<user_id>` (untested; check `references/label-studio/api.md` first).
- If a sync maps annotator ids to names, update that mapping too.
