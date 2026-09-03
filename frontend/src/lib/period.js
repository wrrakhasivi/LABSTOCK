import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

const PeriodContext = createContext(null);

export const usePeriod = () => useContext(PeriodContext);

export const PeriodProvider = ({ children }) => {
  const [periods, setPeriods] = useState([]);
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api.periods().then((data) => {
      setPeriods(data);
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  const refreshPeriods = () => api.periods().then((data) => { setPeriods(data); return data; });

  const value = { periods, year, month, setYear, setMonth, loaded, refreshPeriods };
  return <PeriodContext.Provider value={value}>{children}</PeriodContext.Provider>;
};
