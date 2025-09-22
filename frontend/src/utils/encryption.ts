/**
 * Client-side Encryption Utilities
 * 
 * Provides simple encryption/decryption for client-side data protection.
 * Note: This is for basic XSS protection, not for securing data from sophisticated attacks.
 */

/**
 * Simple XOR-based encryption for client-side data protection
 * This is NOT cryptographically secure but provides basic XSS protection
 */
export function encrypt(text: string, key: string): string {
  if (!text || !key) {
    throw new Error('Text and key are required for encryption')
  }

  try {
    // Convert to base64 first
    const base64Text = btoa(text)
    let encrypted = ''
    
    for (let i = 0; i < base64Text.length; i++) {
      const textChar = base64Text.charCodeAt(i)
      const keyChar = key.charCodeAt(i % key.length)
      encrypted += String.fromCharCode(textChar ^ keyChar)
    }
    
    // Return base64 encoded encrypted string
    return btoa(encrypted)
  } catch (error) {
    console.error('Encryption failed:', error)
    throw new Error('Failed to encrypt data')
  }
}

/**
 * Decrypt XOR-encrypted data
 */
export function decrypt(encryptedText: string, key: string): string {
  if (!encryptedText || !key) {
    throw new Error('Encrypted text and key are required for decryption')
  }

  try {
    // Decode from base64
    const encrypted = atob(encryptedText)
    let decrypted = ''
    
    for (let i = 0; i < encrypted.length; i++) {
      const encryptedChar = encrypted.charCodeAt(i)
      const keyChar = key.charCodeAt(i % key.length)
      decrypted += String.fromCharCode(encryptedChar ^ keyChar)
    }
    
    // Decode from base64
    return atob(decrypted)
  } catch (error) {
    console.error('Decryption failed:', error)
    throw new Error('Failed to decrypt data')
  }
}

/**
 * Secure random string generation
 */
export function generateSecureKey(length: number = 32): string {
  const array = new Uint8Array(length)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * Hash a string using Web Crypto API (for integrity checks)
 */
export async function hashString(text: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(text)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Validate encrypted data integrity
 */
export async function validateIntegrity(data: string, expectedHash?: string): Promise<boolean> {
  if (!expectedHash) return true
  
  try {
    const actualHash = await hashString(data)
    return actualHash === expectedHash
  } catch {
    return false
  }
}