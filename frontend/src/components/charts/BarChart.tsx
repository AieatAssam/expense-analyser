import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { Box } from '@chakra-ui/react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  data: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      backgroundColor?: string | string[];
      borderColor?: string | string[];
      borderWidth?: number;
    }[];
  };
  title?: string;
  height?: number;
  horizontal?: boolean;
  options?: Partial<ChartOptions<'bar'>>;
}

export const BarChart: React.FC<BarChartProps> = ({ 
  data, 
  title, 
  height = 400,
  horizontal = false,
  options = {} 
}) => {
  const defaultOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: horizontal ? 'y' as const : 'x' as const,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: !!title,
        text: title,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.dataset.label || '';
            const value = context.parsed[horizontal ? 'x' : 'y'] || 0;
            return `${label}: $${value.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      [horizontal ? 'x' : 'y']: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return '$' + Number(value).toFixed(2);
          }
        }
      },
    },
    ...options,
  };

  // Generate default colors if not provided
  const generateColors = (count: number) => {
    const colors = [];
    for (let i = 0; i < count; i++) {
      const hue = (i * 137.5) % 360;
      colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    return colors;
  };

  // Apply default styling to datasets
  const styledData = {
    ...data,
    datasets: data.datasets.map((dataset, datasetIndex) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || 
        (Array.isArray(dataset.data) ? generateColors(dataset.data.length) : 
         `hsl(${datasetIndex * 137.5 % 360}, 70%, 60%)`),
      borderColor: dataset.borderColor || 
        (Array.isArray(dataset.data) ? generateColors(dataset.data.length).map(color => 
          color.replace('60%)', '40%)')) : 
         `hsl(${datasetIndex * 137.5 % 360}, 70%, 40%)`),
      borderWidth: dataset.borderWidth ?? 1,
    })),
  };

  return (
    <Box height={`${height}px`} width="100%">
      <Bar data={styledData} options={defaultOptions} />
    </Box>
  );
};