use std::time::Instant;

pub fn fibonacci(n: u32) -> u128 {
    let mut a = 0;
    let mut b = 1;
    for _i in 0..n {
        let c = a + b;
        a = b;
        b = c;
    }
    b
}

fn main() {
    let mut start = Instant::now();
    println!("Hello, world!");
    let mut duration = start.elapsed();
    println!("Time elapsed in {:?}", duration);
    println!("Time elapsed in {:?} seconds", duration.as_nanos());
    println!("Time elapsed in {:?} seconds", duration.as_secs_f64());

    let x: u32 = 186;
    let y: u128;
    start = Instant::now();
    y = fibonacci(x);
    duration = start.elapsed();
    println!("Fibonacci of {:?} is {:}", x, y);
    println!("Time elapsed in {:?}", duration);

    let z: u128 = 2u128.pow(128)+1;
    println!("128^128 = {:?}", z);

}
