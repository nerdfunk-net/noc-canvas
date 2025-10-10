/**
 * Safe JSON parsing utilities to prevent crashes from malformed JSON
 */

/**
 * Safely parse JSON with a fallback value
 * @param jsonString - The JSON string to parse
 * @param fallback - Fallback value if parsing fails
 * @returns Parsed value or fallback
 */
export function safeJSONParse<T>(jsonString: string | null | undefined, fallback: T): T {
  if (!jsonString) {
    return fallback
  }

  try {
    const parsed = JSON.parse(jsonString)

    // Basic validation - ensure we got something
    if (parsed === null || parsed === undefined) {
      return fallback
    }

    return parsed as T
  } catch (error) {
    console.warn('JSON parse failed:', error)
    return fallback
  }
}

/**
 * Safely parse JSON array
 * @param jsonString - The JSON string to parse
 * @param fallback - Fallback array (default: [])
 * @returns Parsed array or fallback
 */
export function safeJSONParseArray<T = any>(
  jsonString: string | null | undefined,
  fallback: T[] = []
): T[] {
  const parsed = safeJSONParse(jsonString, fallback)

  // Ensure result is an array
  if (!Array.isArray(parsed)) {
    console.warn('Parsed value is not an array, returning fallback')
    return fallback
  }

  return parsed
}

/**
 * Safely parse JSON object
 * @param jsonString - The JSON string to parse
 * @param fallback - Fallback object (default: {})
 * @returns Parsed object or fallback
 */
export function safeJSONParseObject<T extends object = Record<string, any>>(
  jsonString: string | null | undefined,
  fallback: T = {} as T
): T {
  const parsed = safeJSONParse(jsonString, fallback)

  // Ensure result is an object
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    console.warn('Parsed value is not an object, returning fallback')
    return fallback
  }

  return parsed as T
}

/**
 * Safely stringify JSON with error handling
 * @param value - Value to stringify
 * @param fallback - Fallback string (default: '{}')
 * @returns JSON string or fallback
 */
export function safeJSONStringify(value: any, fallback: string = '{}'): string {
  try {
    return JSON.stringify(value)
  } catch (error) {
    console.warn('JSON stringify failed:', error)
    return fallback
  }
}
