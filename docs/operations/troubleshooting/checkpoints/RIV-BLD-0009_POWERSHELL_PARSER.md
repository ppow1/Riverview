<!-- Version: 0.5.1 -->
# RIV-BLD-0009 — PowerShell installer parser rejected compressed control syntax

Trigger: PowerShell reports `Missing 'in' after variable in foreach loop` before executing the installer.

Smallest repair: Preserve spaces between the `in` keyword and collection expression and use readable control-flow formatting throughout the outer installer.

Verify: The installer reaches workspace validation before creating or modifying any runtime files.