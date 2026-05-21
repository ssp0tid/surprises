import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Config, GitConfig, EncryptionConfig } from '../types';

interface ConfigSchema {
  sourceDir: string;
  repoUrl: string;
  branch: string;
  encryption: EncryptionConfig;
  git: GitConfig;
}

const defaults: ConfigSchema = {
  sourceDir: path.join(os.homedir(), 'dotfiles'),
  repoUrl: '',
  branch: 'main',
  encryption: {
    enabled: false,
    algorithm: 'aes-256-gcm',
    kdf: 'pbkdf2',
    iterations: 100000,
    keyLength: 32,
  },
  git: {
    authorName: os.userInfo().username,
    authorEmail: '',
    commitMessage: 'Update dotfiles via dot-sync',
    autoCommitInterval: 0,
  },
};

const configDir = path.join(os.homedir(), '.config', 'dot-sync');
const configPath = path.join(configDir, 'config.json');

class ConfigManager {
  private config: ConfigSchema;

  constructor() {
    this.ensureConfigDir();
    this.config = this.loadConfig();
  }

  private ensureConfigDir(): void {
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
  }

  private loadConfig(): ConfigSchema {
    if (fs.existsSync(configPath)) {
      try {
        const data = fs.readFileSync(configPath, 'utf-8');
        const loaded = JSON.parse(data);
        return { ...defaults, ...loaded };
      } catch (e) {
        return { ...defaults };
      }
    }
    return { ...defaults };
  }

  private saveConfig(): void {
    fs.writeFileSync(configPath, JSON.stringify(this.config, null, 2));
  }

  get<K extends keyof ConfigSchema>(key: K): ConfigSchema[K] {
    return this.config[key];
  }

  set<K extends keyof ConfigSchema>(key: K, value: ConfigSchema[K]): void {
    this.config[key] = value;
    this.saveConfig();
  }

  setMultiple(updates: Partial<ConfigSchema>): void {
    this.config = { ...this.config, ...updates };
    this.saveConfig();
  }

  getAll(): ConfigSchema {
    return { ...this.config };
  }

  getConfig(): Config {
    return this.config as Config;
  }

  reset(): void {
    this.config = { ...defaults };
    this.saveConfig();
  }

  has(key: keyof ConfigSchema): boolean {
    return key in this.config;
  }

  delete(key: keyof ConfigSchema): void {
    delete this.config[key];
    this.saveConfig();
  }

  getSourceDir(): string {
    return this.config.sourceDir;
  }

  setSourceDir(dir: string): void {
    this.config.sourceDir = path.resolve(dir);
    this.saveConfig();
  }

  getRepoUrl(): string {
    return this.config.repoUrl;
  }

  setRepoUrl(url: string): void {
    this.config.repoUrl = url;
    this.saveConfig();
  }

  getBranch(): string {
    return this.config.branch;
  }

  setBranch(branch: string): void {
    this.config.branch = branch;
    this.saveConfig();
  }

  getEncryption(): EncryptionConfig {
    return this.config.encryption;
  }

  setEncryption(config: Partial<EncryptionConfig>): void {
    this.config.encryption = { ...this.config.encryption, ...config };
    this.saveConfig();
  }

  getGitConfig(): GitConfig {
    return this.config.git;
  }

  setGitConfig(config: Partial<GitConfig>): void {
    this.config.git = { ...this.config.git, ...config };
    this.saveConfig();
  }
}

export const configManager = new ConfigManager();
