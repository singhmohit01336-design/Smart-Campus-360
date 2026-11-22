import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import Sidebar from '../components/layout/Sidebar';

const DashboardLayout = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar onMobileMenuToggle={() => setMobileMenuOpen((prev) => !prev)} />
      <div className="flex flex-1">
        <Sidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
        <main className="flex-1 lg:pl-64 min-w-0 flex flex-col">
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto flex-1">
            <Outlet />
          </div>
          <footer className="py-4 px-6 text-center text-xs text-slate-400 border-t border-slate-200 bg-white">
            SmartCampus 360 – Cloud-Powered Campus Intelligence & Student Helpdesk Platform © {new Date().getFullYear()}
          </footer>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
