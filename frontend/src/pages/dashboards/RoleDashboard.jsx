import React from 'react';
import { useAuth } from '../../context/AuthContext';
import StudentDashboard from './StudentDashboard';
import FacultyDashboard from './FacultyDashboard';
import TechnicianDashboard from './TechnicianDashboard';
import AdminDashboard from './AdminDashboard';
import SuperadminDashboard from './SuperadminDashboard';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const RoleDashboard = () => {
  const { user, loading } = useAuth();

  if (loading || !user) {
    return <LoadingSpinner text="Authenticating user role..." />;
  }

  const role = (user.role || '').toLowerCase();

  switch (role) {
    case 'superadmin':
      return <SuperadminDashboard user={user} />;
    case 'admin':
      return <AdminDashboard user={user} />;
    case 'technician':
      return <TechnicianDashboard user={user} />;
    case 'faculty':
      return <FacultyDashboard user={user} />;
    case 'student':
    default:
      return <StudentDashboard user={user} />;
  }
};

export default RoleDashboard;
