import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { Box } from '@chakra-ui/react';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartProps {
  data: {
    labels: string[];
    datasets: {
      label?: string;
      data: number[];
      backgroundColor?: string[];
      borderColor?: string[];
      borderWidth?: number;
    }[];
  };
  title?: string;
  height?: number;
  options?: Partial<ChartOptions<'pie'>>;
}

export const PieChart: React.FC<PieChartProps> = ({ 
  data, 
  title, 
  height = 400,
  options = {} 
}) => {
  const defaultOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: !!title,
        text: title,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
          }
        }
      }
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
    datasets: data.datasets.map((dataset) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || generateColors(data.labels.length),
      borderColor: dataset.borderColor || generateColors(data.labels.length).map(color => 
        color.replace('60%)', '40%)')
      ),
      borderWidth: dataset.borderWidth ?? 2,
    })),
  };

  return (
    <Box height={`${height}px`} width="100%">
      <Pie data={styledData} options={defaultOptions} />
    </Box>
  );
};