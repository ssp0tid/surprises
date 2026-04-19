use rand::{rngs::OsRng, Rng, RngCore};
use crate::config::GeneratorConfig;
use crate::entropy::EntropyInfo;
use crate::errors::{PassgenError, Result};

pub fn generate(config: &GeneratorConfig) -> Result<String> {
    if config.length < 8 || config.length > 128 {
        return Err(PassgenError::InvalidLength(config.length));
    }

    if config.pronounceable {
        return generate_pronounceable(config);
    }

    let chars = config.charset();
    if chars.is_empty() {
        return Err(PassgenError::NoCharacterSets);
    }

    if config.no_duplicate && config.length > chars.len() {
        return Err(PassgenError::InsufficientUniqueChars(config.length, chars.len()));
    }

    let mut rng = OsRng;
    let mut buf = vec![0u8; config.length];
    rng.fill_bytes(&mut buf);

    let password: String = if config.no_duplicate {
        let mut available: Vec<char> = chars.clone();
        let mut result = String::new();
        
        for &byte in &buf {
            let idx = byte as usize % available.len();
            result.push(available.remove(idx));
        }
        result
    } else {
        buf.iter()
            .map(|&b| chars[b as usize % chars.len()])
            .collect()
    };

    Ok(password)
}

pub fn generate_multiple(config: &GeneratorConfig, count: usize) -> Result<Vec<String>> {
    (0..count).map(|_| generate(config)).collect()
}

fn generate_pronounceable(config: &GeneratorConfig) -> Result<String> {
    let syllables = config.syllable_count.unwrap_or(3);
    let sep = config.separator.unwrap_or('-');
    
    let consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z'];
    let vowels = ['a', 'e', 'i', 'o', 'u'];
    let endings = ["ax", "ex", "ix", "ox", "ux"];
    
    let mut rng = OsRng;
    let mut parts = Vec::new();
    let mut buf = [0u8; 1];
    
    for _ in 0..syllables {
        let mut syllable = String::new();
        
        rng.fill_bytes(&mut buf);
        let con_start = consonants[buf[0] as usize % consonants.len()];
        syllable.push(con_start);
        
        rng.fill_bytes(&mut buf);
        let vowel = vowels[buf[0] as usize % vowels.len()];
        syllable.push(vowel);
        
        if rng.gen_bool(0.5) {
            rng.fill_bytes(&mut buf);
            let con_end = consonants[buf[0] as usize % consonants.len()];
            syllable.push(con_end);
        }
        
        if rng.gen_bool(0.3) {
            rng.fill_bytes(&mut buf);
            let ending = endings[buf[0] as usize % endings.len()];
            syllable.push(ending.chars().next().unwrap_or('x'));
        }
        
        parts.push(syllable);
    }
    
    let result = parts.join(&sep.to_string());
    let password = if config.length > 0 && config.length < result.len() {
        result[..config.length].to_string()
    } else {
        result
    };
    
    Ok(password)
}

pub fn generate_with_info(config: &GeneratorConfig) -> Result<(String, EntropyInfo)> {
    let password = generate(config)?;
    let charset_size = config.charset_size();
    let entropy_info = EntropyInfo::calculate(&password, charset_size);
    Ok((password, entropy_info))
}