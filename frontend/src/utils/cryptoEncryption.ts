/**
 * Cryptographically Secure Encryption using Web Crypto API
 *
 * This module provides AES-GCM encryption for client-side data protection.
 * Much more secure than XOR-based encryption.
 */

/**
 * Derive a cryptographic key from a password using PBKDF2
 */
async function deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const encoder = new TextEncoder()
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  )

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 100000,
      hash: 'SHA-256'
    },
    passwordKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}

/**
 * Encrypt data using AES-GCM
 *
 * @param plaintext - The text to encrypt
 * @param password - Password used for key derivation
 * @returns Base64-encoded encrypted data with IV and salt prepended
 */
export async function encryptSecure(plaintext: string, password: string): Promise<string> {
  try {
    const encoder = new TextEncoder()
    const data = encoder.encode(plaintext)

    // Generate random salt and IV
    const salt = crypto.getRandomValues(new Uint8Array(16))
    const iv = crypto.getRandomValues(new Uint8Array(12))

    // Derive key from password
    const key = await deriveKey(password, salt)

    // Encrypt data
    const encrypted = await crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      data
    )

    // Combine salt + iv + encrypted data
    const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength)
    combined.set(salt, 0)
    combined.set(iv, salt.length)
    combined.set(new Uint8Array(encrypted), salt.length + iv.length)

    // Convert to base64
    return btoa(String.fromCharCode(...combined))
  } catch (error) {
    console.error('❌ Secure encryption failed:', error)
    throw new Error('Failed to encrypt data securely')
  }
}

/**
 * Decrypt AES-GCM encrypted data
 *
 * @param encryptedData - Base64-encoded encrypted data with IV and salt
 * @param password - Password used for key derivation
 * @returns Decrypted plaintext
 */
export async function decryptSecure(encryptedData: string, password: string): Promise<string> {
  try {
    // Decode from base64
    const combined = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0))

    // Extract salt, IV, and encrypted data
    const salt = combined.slice(0, 16)
    const iv = combined.slice(16, 28)
    const encrypted = combined.slice(28)

    // Derive key from password
    const key = await deriveKey(password, salt)

    // Decrypt data
    const decrypted = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      encrypted
    )

    // Convert to string
    const decoder = new TextDecoder()
    return decoder.decode(decrypted)
  } catch (error) {
    console.error('❌ Secure decryption failed:', error)
    throw new Error('Failed to decrypt data securely')
  }
}

/**
 * Generate a cryptographically secure random key
 */
export function generateSecureKey(length: number = 32): string {
  const array = new Uint8Array(length)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * Check if Web Crypto API is available
 */
export function isCryptoAvailable(): boolean {
  return typeof crypto !== 'undefined' &&
         typeof crypto.subtle !== 'undefined' &&
         typeof crypto.getRandomValues !== 'undefined'
}
