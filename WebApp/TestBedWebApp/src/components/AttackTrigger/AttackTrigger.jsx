import { useEffect, useRef, useState } from 'react';
import { useDispatch } from 'react-redux';
import { graphActions } from '../../store/graph-slice';
import { createSetAttackFactorMsg } from '../../assets/msgForServer'; // adjust path if needed
import useWebSocket from 'react-use-websocket'; // add this at top

export default function AttackTrigger() {
  const dispatch = useDispatch();
  const [isGreenOn, setIsGreenOn] = useState(false);
  const [isRedOn, setIsRedOn] = useState(false);
  const optionIndexRef = useRef(0);
  const redTimeoutRef = useRef(null);
  const offTimeoutRef = useRef(null);
  const { sendJsonMessage } = useWebSocket('ws://127.0.0.1:8765');

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'b' || event.key === 'B') {
        // console.log('B key pressed! Starting attack...');

        // Clear any existing timeouts first
        clearTimeout(redTimeoutRef.current);
        clearTimeout(offTimeoutRef.current);

        let newAttackFactor;
        let attackType;

        switch (optionIndexRef.current) {
          case 0:
            newAttackFactor = Math.random() * (0.75 - 0.7) + 0.7;
            attackType = 'CPU HIGH ATTACK';
            break;
          case 1:
            newAttackFactor = Math.random() * (0.85 - 0.8) + 0.8;
            attackType = 'MAL UP ATTACK';
            break;
          case 2:
            newAttackFactor = 1;
            attackType = 'UNDETECTABLE ATTACK';
            break;
          default:
            newAttackFactor = 1;
            attackType = 'UNKNOWN ATTACK';
        }

        // Turn on green light immediately
        setIsGreenOn(true);
        console.log('Green light ON, attack type:', attackType);
        
        // Send attack factor to backend
        sendJsonMessage(createSetAttackFactorMsg(newAttackFactor));
        dispatch(graphActions.setCurrentAttackFactor(newAttackFactor)); // for frontend state tracking
        
        const timestamp = Math.floor(Date.now() / 1000);

        // Update graph dots immediately (not detected yet)
        ['EPS_BATTERY_TOTAL_VOLTAGE', 'EPS_BATTERY_CURRENT'].forEach((key) => {
          dispatch(
            graphActions.flagRedDotsForKey({
              key,
              factor: newAttackFactor,
              duration: 10,
              isDetected: false, // Initially not detected
            })
          );
        });

        if (attackType === 'UNDETECTABLE ATTACK') {
          // For undetectable attacks, send green command immediately
          console.log('Dispatching UNDETECTABLE ATTACK command');
          const commandPayload = {
            timeCommandSent: timestamp,
            command: attackType,
            isGreen: true,
          };
          console.log('Command payload:', commandPayload);
          dispatch(graphActions.handleNewCommand(commandPayload));

          // Turn off green light after 6 seconds
          offTimeoutRef.current = setTimeout(() => {
            setIsGreenOn(false);
            console.log('Green light OFF (undetectable attack ended)');
          }, 6000);
        } else {
          // For detectable attacks, wait for detection
          const delay = Math.floor(Math.random() * 2000) + 1000;
          console.log(`Detectable attack will be detected in ${delay}ms`);

          redTimeoutRef.current = setTimeout(() => {
            setIsRedOn(true);
            console.log('Red light ON - Attack detected!');

            // Send red command when detected
            const commandPayload = {
              timeCommandSent: Math.floor(Date.now() / 1000),
              command: attackType,
              isRed: true,
            };
            console.log('Command payload:', commandPayload);
            dispatch(graphActions.handleNewCommand(commandPayload));

            // Update graph dots to show as detected (red)
            ['EPS_BATTERY_TOTAL_VOLTAGE', 'EPS_BATTERY_CURRENT'].forEach(
              (key) => {
                dispatch(
                  graphActions.flagRedDotsForKey({
                    key,
                    factor: newAttackFactor,
                    duration: 10,
                    isDetected: true, // Now detected
                  })
                );
              }
            );

            

            // Reset attack factor after duration
            setTimeout(() => {
              dispatch(graphActions.setCurrentAttackFactor(1));
              sendJsonMessage(createSetAttackFactorMsg(1)); // <-- this resets backend too
              console.log('Attack factor reset to 1');
            }, 7000); // 7 seconds

            // Turn off both lights after 6 seconds
            offTimeoutRef.current = setTimeout(() => {
              setIsGreenOn(false);
              setIsRedOn(false);
              console.log('Both lights OFF');
            }, 6000);
          }, delay);
        }

        optionIndexRef.current = (optionIndexRef.current + 1) % 3;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(redTimeoutRef.current);
      clearTimeout(offTimeoutRef.current);
    };
  }, [dispatch, sendJsonMessage]);

  // Return the light states so the component can use them
  return { isGreenOn, isRedOn };
}
