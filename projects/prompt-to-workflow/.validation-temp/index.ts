// Utility functions with Lodash
import _ from 'lodash';

export async function main() {
  const data = [1, 2, 3, 4, 5];

  const doubled = _.map(data, (n) => n * 2);
  console.log('Doubled:', doubled);

  const evens = _.filter(data, (n) => n % 2 === 0);
  console.log('Evens:', evens);

  const sum = _.reduce(data, (acc, n) => acc + n, 0);
  console.log('Sum:', sum);

  return { doubled, evens, sum };
}
