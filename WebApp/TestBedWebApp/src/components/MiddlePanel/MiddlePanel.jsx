import React from 'react';
import GraphBox from '../GraphBox/GraphBox';
import styles from './MiddlePanel.module.css';

const MiddlePanel = ({ data }) => {
  const graphKeys = Object.keys(data);
  if (Object.keys(data).length === 0) {
    return <p>Currently wating for graph data</p>;
  }

  return (
    <div className={styles.middlePanel}>
      <GraphBox
        key={1}
        data={data}
        allKeys={graphKeys}
        defaultGraphKey={graphKeys[0]}
      />
      <GraphBox
        key={2}
        data={data}
        allKeys={graphKeys}
        defaultGraphKey={graphKeys[1]}
      />
      <GraphBox
        key={3}
        data={data}
        allKeys={graphKeys}
        defaultGraphKey={graphKeys[2]}
      />
    </div>
  );
};

export default MiddlePanel;
