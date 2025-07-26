import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Box } from '@chakra-ui/react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface LineChartProps {
  data: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      borderColor?: string;
      backgroundColor?: string;
      tension?: number;
    }[];
  };
  title?: string;
  height?: number;
  options?: Partial<ChartOptions<'line'>>;
}

export const LineChart: React.FC<LineChartProps> = ({ 
  data, 
  title, 
  height = 400,
  options = {} 
}) => {
  const defaultOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: !!title,
        text: title,
      },
    },
    scales: {
      y: {
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

  // Apply default styling to datasets
  const styledData = {
    ...data,
    datasets: data.datasets.map((dataset, index) => ({
      ...dataset,
      borderColor: dataset.borderColor || `hsl(${index * 137.5 % 360}, 70%, 50%)`,
      backgroundColor: dataset.backgroundColor || `hsla(${index * 137.5 % 360}, 70%, 50%, 0.1)`,
      tension: dataset.tension ?? 0.4,
    })),
  };

  return (
    <Box height={`${height}px`} width="100%">
      <Line data={styledData} options={defaultOptions} />
    </Box>
  );
};