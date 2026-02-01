const EmptyState = ({ title, description, icon: Icon, action }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 bg-gray-800/50 border border-gray-700 rounded-lg">
      {Icon && <Icon className="w-16 h-16 text-gray-600 mb-4" />}
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-center mb-6 max-w-md">{description}</p>
      {action}
    </div>
  );
};

export default EmptyState;
