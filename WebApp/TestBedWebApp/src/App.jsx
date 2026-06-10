import { RouterProvider, createBrowserRouter } from 'react-router-dom';

import HomePage from './pages/Home';
import SimConfigPage from './pages/SimConfig';
import ErrorPage from './pages/Error';
import { action as simConfigAction } from './components/SimParamForm/SimParamForm.jsx';

import SimPage from './pages/SimPage/Sim.jsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <SimConfigPage />,
    errorElement: <ErrorPage />,
    action: simConfigAction
  },
  {
    path: '/SimConfig',
    element: <SimConfigPage />,
    action: simConfigAction,
  },
  {
    path: '/sim',
    element: <SimPage />,
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
