# Zero-cloud execution policy

This public repository must be safe to browse, clone, fork and run locally. It contains synthetic data only and no credentials, tenant identifiers, account locators, connection strings or deployable cloud target. CI has read-only repository permission on standard Ubuntu runners and executes only local validation. The safety scanner rejects deployment/authentication commands in executable surfaces.

No Snowflake, Fabric, Azure, Power BI Service or other paid account is needed. Never add cloud secrets, an authenticated profile, a manual deployment workflow, `id-token: write`, a self-hosted runner, or a cloud execution step. A real warehouse or mirror would be chargeable; designing it in Markdown does not create it. Public forks cannot access the owner's billing account without separately supplied credentials, and none are present here.
