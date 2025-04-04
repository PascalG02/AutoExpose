This folder stores the different workflows/GitHub actions used in the SQL Deployment Project.

PHASE 1 - Auto Deploy SQL script to create a database , a table and insert values. Make use of a tunnel service and create a user to log remotely.
PHASE 2- Advance the workflow to now include environments (Developer and Production), you and your AP. It should deploy the script to both services and have a request in between deployments.
PHASE 3- To avoid repitition in workflow, create a template and call workflow to do phase 2. Also add try/catch statements.


Requirements for execution:
1. Pinggy ssh command for a TCP tunnel on Port - 1433 (Run on local to get server url).
[ssh -p 443 -R0:localhost:1433 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 01demL9J8P2+tcp@free.pinggy.io]

2. User created on management to access database - sysadmin for full access

3. Secret variables with login details for both dev and prod - 
[Server_URL (value with "," and not ":" at the end for port), Username, Password]

4. SQL script & path on github to deploy changes using set script on execution
