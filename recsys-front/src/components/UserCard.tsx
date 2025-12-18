import { useEffect, useState } from "react";
import { getUsers } from "../api/items";
import type { User } from "../types/Responses";

interface UserCardProps {
  currentUserId?: number;
  onUserChange?: (id: number) => void;
}

const defaultUser: User = {
  id: 0,
  name: "Gabriel",
  email: "",
  picture: "https://media.licdn.com/dms/image/v2/D4D03AQEP4Ky4aNOgig/profile-displayphoto-crop_800_800/B4DZntcQjrJIAI-/0/1760625232558?e=1767830400&v=beta&t=LhKD4H0SRkg-gqQcZT97G2-hHXGbIu_a_BYF5DzboDU",
};

export default function UserCard({
  currentUserId,
  onUserChange,
}: UserCardProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [user, setUser] = useState<User>(defaultUser);

  useEffect(() => {
    if (!currentUserId || users.length === 0) {
      setUser(defaultUser);
      return;
    }

    const selectedUser = users.find((u) => u.id === currentUserId);
    setUser(selectedUser ?? defaultUser);
  }, [currentUserId, users]);

  useEffect(() => {
    (async () => {
      try {
        const usersResponse = await getUsers();
        setUsers(usersResponse);
      } catch (error) {
        console.error("Failed to fetch users:", error);
      }
    })();
  }, []);

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-white border border-gray-200 rounded-xl shadow-sm w-full overflow-hidden">
      <div className="flex items-center gap-4 w-full">
        <img
          src={user.picture}
          className="w-16 h-16 rounded-full object-cover shadow"
        />
      </div>

      {onUserChange && (
        <div className="w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Selecionar usuário (ID)
          </label>

          <select
            value={currentUserId ?? ""}
            onChange={(e) => onUserChange(Number(e.target.value))}
            className="
              w-full px-3 py-2 border border-gray-300 rounded-lg
              bg-gray-50 text-gray-800 shadow-sm
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              transition cursor-pointer
            "
          >
            {users.map((user) => {
              return (
                <option key={user.id} value={user.id}>
                  {user.id}
                </option>
              );
            })}
          </select>
        </div>
      )}
    </div>
  );
}
