interface UserCardProps {
  name: string;
  email: string;
  role?: string;
  avatarUrl?: string;
  currentUserId?: number;
  onUserChange?: (id: number) => void;
}

export default function UserCard({
  name,
  email,
  role = "Usuário",
  avatarUrl = "https://via.placeholder.com/150",
  currentUserId,
  onUserChange,
}: UserCardProps) {
  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-white border border-gray-200 rounded-xl shadow-sm w-full">
      {/* FOTO E INFO */}
      <div className="flex items-center gap-4 w-full">
        <img
          src={avatarUrl}
          alt={name}
          className="w-16 h-16 rounded-full object-cover shadow"
        />

        <div className="flex flex-col">
          <span className="text-lg font-semibold text-gray-900">{name}</span>
          <span className="text-sm text-gray-600">{email}</span>
          <span className="text-xs mt-1 px-2 py-0.5 bg-gray-200 text-gray-700 rounded-full w-fit">
            {role}
          </span>
        </div>
      </div>

      {/* SELETOR DE ID */}
      {onUserChange && (
        <div className="w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Selecionar usuário (ID)
          </label>

          <select
            value={currentUserId}
            onChange={(e) => onUserChange(Number(e.target.value))}
            className="
              w-full px-3 py-2 border border-gray-300 rounded-lg 
              bg-gray-50 text-gray-800 shadow-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              transition
            "
          >
            {[...Array(70)].map((_, i) => {
              const id = 1001 + i;
              return (
                <option key={id} value={id}>
                  {id}
                </option>
              );
            })}
          </select>
        </div>
      )}
    </div>
  );
}
