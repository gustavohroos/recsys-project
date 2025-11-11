interface UserCardProps {
  name: string;
  email: string;
  role?: string;
  avatarUrl?: string;
}

export default function UserCard({
  name,
  email,
  role = "Usuário",
  avatarUrl = "https://via.placeholder.com/150",
}: UserCardProps) {
  return (
    <div className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
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
  );
}
