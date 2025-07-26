// Mock date-fns
module.exports = {
  format: jest.fn((date, formatStr) => {
    if (typeof date === 'string') {
      return date;
    }
    return '2024-01-15'; // Mock formatted date
  }),
  subDays: jest.fn((date, days) => new Date('2024-01-15')),
  subWeeks: jest.fn((date, weeks) => new Date('2024-01-15')),
  subMonths: jest.fn((date, months) => new Date('2024-01-15')),
  startOfDay: jest.fn((date) => new Date('2024-01-15')),
};