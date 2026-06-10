import SimParamForm from '../components/SimParamForm/SimParamForm';
import './panel.css';
import { useDispatch, useSelector } from 'react-redux';
import { simActions } from '../store/sim-slice';


export default function SimConfigPage() {
  const dispatch = useDispatch();
  const simulationCompleted = useSelector(
    (state) => state.sim.simulationCompleted
  );
  const completionMessage = useSelector((state) => state.sim.completionMessage);

  return (
    <>
      {simulationCompleted && (
        <div className="completion-modal-overlay">
          <div className="completion-modal">
            <h2>Simulation Ended</h2>
            <p>{completionMessage}</p>
            <button
              type="button"
              onClick={() => dispatch(simActions.dismissCompletion())}
            >
              Close
            </button>
          </div>
        </div>
      )}
      <SimParamForm />
    </>
  );
}
