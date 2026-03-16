---
description: Update chainforge_node with the latest downloaded zip from the platform
---
This workflow automates the process of updating the ChainForge node codebase inside the certificate verification system based on the latest downloaded zip.

// turbo-all
1. Find the latest `chain_*.zip` file downloaded in `c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\` or `c:\Users\ARTH PATEL\Downloads\`.
2. Extract the contents of the latest zip file into a temporary folder `temp_extract` in `c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\`.
3. Delete all existing contents in `c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system\chainforge_node\`.
4. Move all contents from `temp_extract` into the emptied `chainforge_node` folder.
5. Delete the temporary folder `temp_extract`.
