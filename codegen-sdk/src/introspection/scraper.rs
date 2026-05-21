use anyhow::Result;

pub struct HtmlScraper;

impl HtmlScraper {
    pub fn scrape(_url: &str) -> Result<String> {
        anyhow::bail!("Scraping not yet implemented")
    }
}
