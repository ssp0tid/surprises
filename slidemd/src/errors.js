export class SlideMDError extends Error {
  constructor(message, code = 'UNKNOWN', context = {}) {
    super(message);
    this.name = 'SlideMDError';
    this.code = code;
    this.context = context;
  }
}

export class FileNotFoundError extends SlideMDError {
  constructor(path) {
    super(`Input file '${path}' not found`, 'FILE_NOT_FOUND', { path });
    this.name = 'FileNotFoundError';
  }
}

export class InvalidMarkdownError extends SlideMDError {
  constructor(reason, line = null) {
    super(reason, 'INVALID_MARKDOWN', { line });
    this.name = 'InvalidMarkdownError';
  }
}

export class InvalidFrontmatterError extends SlideMDError {
  constructor(reason) {
    super(`Invalid frontmatter: ${reason}`, 'INVALID_FRONTMATTER', { reason });
    this.name = 'InvalidFrontmatterError';
  }
}

export class ThemeNotFoundError extends SlideMDError {
  constructor(name, available) {
    super(`Theme '${name}' not found. Available: ${available.join(', ')}`, 'THEME_NOT_FOUND', { name, available });
    this.name = 'ThemeNotFoundError';
  }
}

export class InvalidThemeError extends SlideMDError {
  constructor(reason) {
    super(`Invalid theme: ${reason}`, 'INVALID_THEME', { reason });
    this.name = 'InvalidThemeError';
  }
}

export class EmptyPresentationError extends SlideMDError {
  constructor() {
    super('No slides found in input file', 'EMPTY_PRESENTATION', {});
    this.name = 'EmptyPresentationError';
  }
}

export class ValidationError extends SlideMDError {
  constructor(field, reason) {
    super(`Validation failed: ${field} - ${reason}`, 'VALIDATION_ERROR', { field, reason });
    this.name = 'ValidationError';
  }
}

export function handleError(error) {
  if (error instanceof SlideMDError) {
    console.error(`Error [${error.code}]: ${error.message}`);
    return error.code;
  }
  console.error(`Error: ${error.message}`);
  return 'UNKNOWN';
}

export function validateInput(options) {
  const errors = [];

  if (options.maxFileSize && options.fileSize > options.maxFileSize) {
    errors.push(new ValidationError('fileSize', `exceeds maximum of ${options.maxFileSize} bytes`));
  }

  if (options.maxSlides && options.slideCount > options.maxSlides) {
    errors.push(new ValidationError('slideCount', `exceeds maximum of ${options.maxSlides}`));
  }

  if (options.aspectRatio) {
    const validRatios = ['16:9', '16:10', '4:3', '1:1'];
    if (!validRatios.includes(options.aspectRatio)) {
      errors.push(new ValidationError('aspectRatio', `must be one of: ${validRatios.join(', ')}`));
    }
  }

  return errors;
}