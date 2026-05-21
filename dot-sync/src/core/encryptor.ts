import * as crypto from 'crypto';

export interface EncryptedData {
  ciphertext: string;
  iv: string;
  salt: string;
  tag: string;
  iterations: number;
}

export interface EncryptorOptions {
  algorithm?: string;
  keyLength?: number;
  ivLength?: number;
  saltLength?: number;
  iterations?: number;
  digest?: string;
}

const DEFAULT_OPTIONS: Required<EncryptorOptions> = {
  algorithm: 'aes-256-gcm',
  keyLength: 32,
  ivLength: 16,
  saltLength: 32,
  iterations: 100000,
  digest: 'sha256',
};

export class Encryptor {
  private options: Required<EncryptorOptions>;
  private password: string;

  constructor(password: string, options: EncryptorOptions = {}) {
    this.password = password;
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  private deriveKey(salt: Buffer, iterations: number): Buffer {
    return crypto.pbkdf2Sync(
      this.password,
      salt,
      iterations,
      this.options.keyLength,
      this.options.digest
    );
  }

  encrypt(plaintext: string): EncryptedData {
    const salt = crypto.randomBytes(this.options.saltLength);
    const iv = crypto.randomBytes(this.options.ivLength);
    const key = this.deriveKey(salt, this.options.iterations);

    const cipher = crypto.createCipheriv(
      this.options.algorithm,
      key,
      iv
    ) as crypto.CipherGCM;

    const ciphertext = Buffer.concat([
      cipher.update(plaintext, 'utf8'),
      cipher.final(),
    ]);

    const tag = cipher.getAuthTag();

    return {
      ciphertext: ciphertext.toString('base64'),
      iv: iv.toString('base64'),
      salt: salt.toString('base64'),
      tag: tag.toString('base64'),
      iterations: this.options.iterations,
    };
  }

  decrypt(data: EncryptedData): string {
    const salt = Buffer.from(data.salt, 'base64');
    const iv = Buffer.from(data.iv, 'base64');
    const ciphertext = Buffer.from(data.ciphertext, 'base64');
    const tag = Buffer.from(data.tag, 'base64');

    const key = this.deriveKey(salt, data.iterations);

    const decipher = crypto.createDecipheriv(
      this.options.algorithm,
      key,
      iv
    ) as crypto.DecipherGCM;

    decipher.setAuthTag(tag);

    const plaintext = Buffer.concat([
      decipher.update(ciphertext),
      decipher.final(),
    ]);

    return plaintext.toString('utf8');
  }

  encryptFile(filePath: string): EncryptedData {
    const fs = require('fs');
    const plaintext = fs.readFileSync(filePath, 'utf8');
    return this.encrypt(plaintext);
  }

  decryptToFile(data: EncryptedData, outputPath: string): void {
    const fs = require('fs');
    const plaintext = this.decrypt(data);
    fs.writeFileSync(outputPath, plaintext, 'utf8');
  }

  encryptBuffer(buffer: Buffer): EncryptedData {
    return this.encrypt(buffer.toString('base64'));
  }

  decryptBuffer(data: EncryptedData): Buffer {
    const base64 = this.decrypt(data);
    return Buffer.from(base64, 'base64');
  }

  verify(data: EncryptedData): boolean {
    try {
      this.decrypt(data);
      return true;
    } catch {
      return false;
    }
  }

  createChild(options?: Partial<EncryptorOptions>): Encryptor {
    return new Encryptor(this.password, {
      ...this.options,
      ...options,
    });
  }
}

export function encrypt(plaintext: string, password: string): EncryptedData {
  const encryptor = new Encryptor(password);
  return encryptor.encrypt(plaintext);
}

export function decrypt(data: EncryptedData, password: string): string {
  const encryptor = new Encryptor(password);
  return encryptor.decrypt(data);
}