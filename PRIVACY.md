# Garry Bot - Privacy Policy

_Last updated: 2026-08-08_

Garry is a Discord bot operated for a single Discord server. This policy explains what data it accesses and stores.

## Data We Store

Garry stores a minimal amount of data locally, in an encrypted database used only by the bot:

- **The Discord User ID of the current "Garry"** — the member currently holding the rotating Garry role.
- **A timestamp** of when the role was last assigned.

This database is encrypted at rest and stored on the server that runs the bot (a privately-managed Ubuntu VPS hosted with Hetzner). No message content, message history, or other personal data is stored in this database.

## Data We Access But Do Not Store

To operate, Garry reads the following live from Discord (via the Discord API) on an as-needed basis, and does not persist it:

- Member list, roles, and online/offline status, to determine who is eligible to become "Garry." Only members who have opted into the Garry nomination pool (by taking the "Nominated" role) are checked. You can leave the pool at any time with the `/optout` command, which removes your Nominated role and excludes you from future eligibility/presence checks.
- Message content and attachments sent by the current "Garry" in a specific channel, which are relayed via webhook to a private archive channel visible only to server staff (moderators and helpers) in the same server, for moderation purposes. This content is stored by Discord as ordinary channel messages, governed by Discord's own retention and [Privacy Policy](https://discord.com/privacy), not by Garry separately.
- Message edit events in that same channel. Since users can still edit their own past messages there at any time (including messages from a previous round they were Garry in), any edited message is deleted to prevent someone from retroactively altering what the historical record shows they said.

## Data We Do Not Collect

Garry does not collect or store presence/activity data, DMs, message content outside the specific channel described above, or any data for users outside the single server it operates in.

## Data Sharing

Garry does not share, sell, or transmit any stored data to third parties. All data remains within the local database used to run the bot and within Discord itself.

## Data Retention & Deletion

The two stored fields (current Garry user ID, last-picked timestamp) are overwritten each time the role rotates and are not retained historically. To request removal of your Discord User ID from the current-Garry field, contact the server administrator.

## Changes to This Policy

If this policy changes, the "Last updated" date at the top will be revised. Continued use of Garry after changes are posted constitutes acceptance of the revised policy.

## Contact

Discord: @.subs
Email: subsical@gmail.com