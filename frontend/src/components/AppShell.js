import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Table2, FlaskConical, Database, FileText, PackageCheck,
  BookOpen, Menu, X, RefreshCw, Activity, LogOut, ShieldCheck, Eye, Users, Settings, LineChart,
} from 'lucide-react';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';
import { usePeriod } from '../lib/period';
import { useAuth } from '../lib/auth';
import { ChangePasswordButton } from './ChangePasswordDialog';
import { ThemeToggleButton } from './ThemeToggle';
import { MONTHS_ID } from '../lib/api';

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, slug: 'dashboard', end: true },
  { to: '/analitik', label: 'Analitik', icon: LineChart, slug: 'analitik' },
  { to: '/pemantauan', label: 'Pemantauan Stok', icon: Table2, slug: 'pemantauan' },
  { to: '/master-reagen', label: 'Master Reagen', icon: FlaskConical, slug: 'master-reagen' },
  { to: '/data-lis', label: 'Data LIS', icon: Database, slug: 'data-lis' },
  { to: '/prf', label: 'PRF', icon: FileText, slug: 'prf' },
  { to: '/penerimaan', label: 'Penerimaan', icon: PackageCheck, slug: 'penerimaan' },
  { to: '/analisis-excel', label: 'Analisis Struktur Excel', icon: BookOpen, slug: 'analisis-excel' },
  { to: '/pengguna', label: 'Kelola Pengguna', icon: Users, slug: 'pengguna', koordinatorOnly: true },
  { to: '/pengaturan', label: 'Pengaturan', icon: Settings, slug: 'pengaturan', koordinatorOnly: true },
];

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/analitik': 'Analitik',
  '/pemantauan': 'Pemantauan Stok',
  '/master-reagen': 'Master Reagen',
  '/data-lis': 'Data LIS',
  '/prf': 'PRF (Purchase Request)',
  '/penerimaan': 'Penerimaan Barang',
  '/analisis-excel': 'Analisis Struktur Excel',
  '/pengguna': 'Kelola Pengguna',
  '/pengaturan': 'Pengaturan',
};

const SidebarContent = ({ onNavigate }) => {
  const { isKoordinator } = useAuth();
  const navItems = NAV.filter((item) => !item.koordinatorOnly || isKoordinator);
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 h-14 border-b">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <FlaskConical className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-bold tracking-tight">LabStock</div>
          <div className="text-[10px] text-muted-foreground">Stok Reagen Lab PK</div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-2 overflow-y-auto" data-testid="app-sidebar">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onNavigate}
              data-testid={`sidebar-nav-item-${item.slug}`}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-accent text-accent-foreground font-medium'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <div className="border-t p-3 text-[10px] text-muted-foreground">
        <div className="flex items-center gap-1"><Activity className="h-3 w-3" /> Sumber: Excel PEMANTAUAN STOCK REAGEN LAB PK</div>
      </div>
    </div>
  );
};

const UserBadge = () => {
  const { user, logout, isKoordinator } = useAuth();
  if (!user) return null;
  return (
    <div className="flex items-center gap-1" data-testid="user-badge">
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
          isKoordinator ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
        }`}
        data-testid="user-role-badge"
      >
        {isKoordinator ? <ShieldCheck className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
        {user.username} · {isKoordinator ? 'Koordinator' : 'Petugas'}
      </span>
      <ChangePasswordButton />
      <ThemeToggleButton />
      <Button variant="ghost" size="sm" onClick={logout} data-testid="logout-button" title="Keluar">
        <LogOut className="h-4 w-4" />
      </Button>
    </div>
  );
};

const PeriodSelector = () => {
  const { periods, year, month, setYear, setMonth } = usePeriod();
  const currentYear = new Date().getFullYear();
  const yearSet = new Set(periods.map((p) => p.year));
  yearSet.add(currentYear);
  yearSet.add(year);
  const yearList = Array.from(yearSet).sort((a, b) => b - a);
  return (
    <div className="flex items-center gap-2">
      <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
        <SelectTrigger className="h-9 w-[130px]" data-testid="period-month-select">
          <SelectValue placeholder="Bulan" />
        </SelectTrigger>
        <SelectContent>
          {MONTHS_ID.slice(1).map((name, idx) => (
            <SelectItem key={idx + 1} value={String(idx + 1)}>{name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
        <SelectTrigger className="h-9 w-[100px]" data-testid="period-year-select">
          <SelectValue placeholder="Tahun" />
        </SelectTrigger>
        <SelectContent>
          {yearList.map((y) => (
            <SelectItem key={y} value={String(y)}>{y}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

export const AppShell = ({ children }) => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || 'LabStock';

  return (
    <div className="App min-h-screen bg-background text-foreground">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[260px] border-r bg-card lg:block">
        <SidebarContent />
      </aside>

      <div className="lg:pl-[260px]">
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b bg-background/85 px-3 backdrop-blur sm:px-4 lg:px-6">
          <div className="flex items-center gap-2">
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <button className="lg:hidden inline-flex h-9 w-9 items-center justify-center rounded-md border" data-testid="mobile-menu-button">
                  {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[260px] p-0">
                <SidebarContent onNavigate={() => setOpen(false)} />
              </SheetContent>
            </Sheet>
            <h1 className="text-base font-semibold tracking-tight sm:text-lg" data-testid="page-title">{title}</h1>
          </div>
          <div className="flex items-center gap-3">
            <PeriodSelector />
            <UserBadge />
          </div>
        </header>

        <main className="px-3 py-4 sm:px-4 lg:px-6">{children}</main>
      </div>
    </div>
  );
};
