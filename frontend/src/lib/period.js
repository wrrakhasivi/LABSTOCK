import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

const PeriodContext = createContext(null);

export const usePeriod = () => useContext(PeriodContext);

export const PeriodProvider = ({ children }) => {
  const [periods, setPeriods] = useState([]);
  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(8);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api.periods().then((data) => {
      setPeriods(data);
      if (data && data.length) {
        setYear(data[0].year);
        setMonth(data[0].month);
      }
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  const value = { periods, year, month, setYear, setMonth, loaded };
  return <PeriodContext.Provider value={value}>{children}</PeriodContext.Provider>;
};
