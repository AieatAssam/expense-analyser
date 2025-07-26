// Mock react-chartjs-2
const React = require('react');

const Line = React.forwardRef((props, ref) => {
  return React.createElement('div', { 
    'data-testid': 'line-chart', 
    ref,
    'data-chart-data': JSON.stringify(props.data),
    'data-chart-options': JSON.stringify(props.options)
  }, 'Line Chart');
});

const Bar = React.forwardRef((props, ref) => {
  return React.createElement('div', { 
    'data-testid': 'bar-chart', 
    ref,
    'data-chart-data': JSON.stringify(props.data),
    'data-chart-options': JSON.stringify(props.options)
  }, 'Bar Chart');
});

const Pie = React.forwardRef((props, ref) => {
  return React.createElement('div', { 
    'data-testid': 'pie-chart', 
    ref,
    'data-chart-data': JSON.stringify(props.data),
    'data-chart-options': JSON.stringify(props.options)
  }, 'Pie Chart');
});

module.exports = {
  Line,
  Bar,
  Pie,
};