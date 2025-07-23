const React = require('react');

const createMockIcon = (name) => {
  const Icon = React.forwardRef((props, ref) => {
    return React.createElement('span', { 
      ...props, 
      ref,
      'data-testid': `mock-icon-${name}`,
      className: [props.className, `mock-icon-${name.toLowerCase()}`].filter(Boolean).join(' ')
    });
  });
  Icon.displayName = name;
  return Icon;
};

module.exports = {
  FiCheckCircle: createMockIcon('FiCheckCircle'),
  FiAlertCircle: createMockIcon('FiAlertCircle'),
  FiClock: createMockIcon('FiClock'),
  FiLoader: createMockIcon('FiLoader'),
  FiUpload: createMockIcon('FiUpload'),
  FiCamera: createMockIcon('FiCamera'),
  FiFile: createMockIcon('FiFile'),
  FiUser: createMockIcon('FiUser'),
  FiSettings: createMockIcon('FiSettings'),
  FiLogOut: createMockIcon('FiLogOut'),
  FiLogIn: createMockIcon('FiLogIn')
};
