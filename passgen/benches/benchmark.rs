use criterion::{criterion_group, criterion_main, Criterion, Bencher};
use passgen::config::GeneratorConfig;
use passgen::generator;

fn bench_generate(c: &mut Criterion) {
    let config = GeneratorConfig::default();
    
    c.bench_function("generate_password", |b| {
        b.iter(|| generator::generate(&config).unwrap())
    });
}

criterion_group!(benches, bench_generate);
criterion_main!(benches);