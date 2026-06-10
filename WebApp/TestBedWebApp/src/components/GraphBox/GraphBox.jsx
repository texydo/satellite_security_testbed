import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import styles from './GraphBox.module.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

const GraphBox = ({ data, allKeys, defaultGraphKey }) => {
  const [selectedKey, setSelectedKey] = useState(defaultGraphKey);
  const graphData = data[selectedKey];

  const [redIndices, setRedIndices] = useState(new Set());
  const [redExpireTimes, setRedExpireTimes] = useState([]); // [{ index, expireAt }]

  // Get the last 100 data points
  const getLastNPoints = (xValues, yValues, n = 100) => {
    if (!xValues || !yValues) return { x: [], y: [] };
    if (xValues.length <= n) {
      return { x: xValues, y: yValues };
    }
    const startIndex = xValues.length - n;
    return {
      x: xValues.slice(startIndex),
      y: yValues.slice(startIndex),
    };
  };

  const limitedData = getLastNPoints(
    graphData?.x_values || [],
    graphData?.y_values || []
  );

  const [modifiedY, setModifiedY] = useState(limitedData.y);

  // // Apply attack factor and red dot coloring
  useEffect(() => {
    setModifiedY(limitedData.y);
  }, [limitedData.y]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'b' || event.key === 'B') {
        const now = Date.now();
        const attackFactor = 4;
        const updatedRedIndices = new Set();
        const updatedExpireTimes = [];
        const newY = [...limitedData.y];

        limitedData.y.forEach((val, i) => {
          updatedRedIndices.add(i);
          updatedExpireTimes.push({
            index: i,
            expireAt: now + 7000,
            factor: attackFactor,
          });
          newY[i] = val * attackFactor;
        });

        setModifiedY(newY);
        setRedIndices(updatedRedIndices);
        setRedExpireTimes(updatedExpireTimes);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [limitedData.y]);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const stillActive = redExpireTimes.filter(
        ({ expireAt }) => expireAt > now
      );
      setRedExpireTimes(stillActive);
      setRedIndices(new Set(stillActive.map(({ index }) => index)));
    }, 500);

    return () => clearInterval(interval);
  }, [redExpireTimes]);

  const chartData = {
    labels: limitedData.x.map((ts) => new Date(ts * 1000)),
    datasets: [
      {
        label: selectedKey,
        data: modifiedY,
        borderColor: 'rgb(0, 191, 255)',
        backgroundColor: 'rgba(0, 191, 255, 0.2)',
        pointRadius: 3, // disables the circle markers
        pointBackgroundColor: (ctx) =>
          redIndices.has(ctx.dataIndex) ? 'red' : 'rgba(0, 191, 255, 1)',
        segment: {
          borderColor: (ctx) =>
            redIndices.has(ctx.p0DataIndex) ? 'red' : 'rgb(0, 191, 255)',
        },
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false, // Critical for proper sizing
    // animation: false,
    animation: {
      duration: 0.3, // smooth transition
      easing: 'linear',
    },
    plugins: {
      legend: {
        display: true,
        labels: {
          color: '#ccc',
          boxWidth: 10, // Smaller legend boxes
          font: { size: 10 }, // Smaller font for legend
        },
      },
      title: { display: false },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'minute',
          tooltipFormat: 'yyyy-MM-dd HH:mm:ss',
        },
        ticks: {
          color: '#ccc',
          maxRotation: 0, // Prevent label rotation
          autoSkip: true, // Skip labels that would overlap
          font: { size: 9 }, // Smaller font for axes
        },
      },
      y: {
        ticks: {
          color: '#ccc',
          font: { size: 9 },
          padding: 0,
          callback: (value) => {
            const numericValue = Number(value);

            if (!Number.isFinite(numericValue)) {
              return value;
            }

            return numericValue.toLocaleString(undefined, {
              maximumFractionDigits: 3,
            });
          },
        },

        afterFit: (scaleInstance) => {
          scaleInstance.width = 44;
        },
      },
    },
  };

  return (
    <div className={styles.graphBox}>
      <div className={styles.header}>
        <h3>{selectedKey}</h3>
        <select
          className={styles.dropdown}
          value={selectedKey}
          onChange={(e) => setSelectedKey(e.target.value)}
        >
          {allKeys.map((key, i) => (
            <option key={i} value={key}>
              {key}
            </option>
          ))}
        </select>
      </div>
      <div className={styles.chartContainer}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};

export default GraphBox;
