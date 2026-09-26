export function defaultRouteForRole(role) {
  switch (role) {
    case 'admin':
      return '/admin'
    case 'candidate':
      return '/candidate'
    case 'interviewer':
      return '/interviewer'
    default:
      return '/login'
  }
}
