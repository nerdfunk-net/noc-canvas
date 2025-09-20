# Local Database Setup

This directory contains the local databases for storing credentials and settings.

## Database Files

### `credentials.db`
Stores user credentials with the following schema:
- **id**: Primary key (integer)
- **owner**: Username of the credential owner (string)
- **name**: Human-readable name for the credential (string)
- **username**: The actual username for the credential (string) 
- **encrypted_password**: AES-encrypted password (text)
- **created_at**: Timestamp when created
- **updated_at**: Timestamp when last modified

### `settings.db`
Stores application settings with the following schema:
- **id**: Primary key (integer)
- **owner**: Username of the setting owner (string)
- **category**: Setting category (nautobot, checkmk, canvas, etc.)
- **key**: Setting key name (string)
- **value**: Setting value as JSON string (text)
- **is_encrypted**: Whether the value is encrypted (boolean)
- **description**: Optional description (text)
- **created_at**: Timestamp when created
- **updated_at**: Timestamp when last modified

## Security Features

1. **Password Encryption**: All passwords are encrypted using Fernet (AES 128) encryption
2. **Key Management**: Encryption key is stored in `.encryption_key` file with restrictive permissions (600)
3. **User Isolation**: Each user can only access their own credentials and settings
4. **Encrypted Settings**: Sensitive settings (tokens, passwords) are automatically encrypted

## Database Location

The databases are stored in:
```
./data/settings/
├── credentials.db
├── settings.db
└── .encryption_key (created automatically)
```

## Initialization

Run the following command from the project root to initialize the databases:
```bash
python init_databases.py
```

## Migration from Old Storage

The new local database system replaces the previous JSON-based storage in the main application database. When you first run the updated application, existing credentials and settings will need to be manually migrated or re-entered.

## Backup

To backup your data:
1. Copy the entire `./data/settings/` directory
2. Make sure to include the `.encryption_key` file - without it, encrypted data cannot be decrypted

## API Endpoints

The following endpoints interact with the local databases:

### Credentials
- `GET /api/settings/credentials` - Get user credentials
- `POST /api/settings/credentials` - Save user credentials
- `POST /api/settings/credentials/add` - Add single credential  
- `DELETE /api/settings/credentials/{id}` - Delete credential

### Settings  
- `GET /api/settings/unified` - Get all user settings
- `POST /api/settings/unified` - Save unified settings
- `POST /api/settings/test-nautobot` - Test Nautobot connection
- `POST /api/settings/test-checkmk` - Test CheckMK connection