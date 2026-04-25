CREATE TABLE "Field"(
    "id" bigserial NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "Field" ADD PRIMARY KEY("id");
ALTER TABLE
    "Field" ADD CONSTRAINT "field_name_unique" UNIQUE("name");
CREATE TABLE "Specialization"(
    "id" bigserial NOT NULL,
    "field_id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "Specialization" ADD CONSTRAINT "specialization_field_id_name_unique" UNIQUE("field_id", "name");
ALTER TABLE
    "Specialization" ADD PRIMARY KEY("id");
CREATE TABLE "User"(
    "id" bigserial NOT NULL,
    "username" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "bio" TEXT NOT NULL,
    "account_type" VARCHAR(20) NOT NULL,
    "specialization_id" BIGINT NOT NULL,
    "level" VARCHAR(20) NOT NULL,
    "workload_hours_per_week" SMALLINT NOT NULL,
    "work_format" VARCHAR(20) NOT NULL,
    "city" VARCHAR(255) NOT NULL,
    "avatar" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "theme" VARCHAR(20) NOT NULL DEFAULT 'light',
    "telegram" VARCHAR(100) NULL,
    "instagram" VARCHAR(100) NULL,
    "behance" VARCHAR(100) NULL,
    "is_superuser" BOOLEAN NOT NULL DEFAULT FALSE
);
ALTER TABLE
    "User" ADD PRIMARY KEY("id");
ALTER TABLE
    "User" ADD CONSTRAINT "user_username_unique" UNIQUE("username");
ALTER TABLE
    "User" ADD CONSTRAINT "user_email_unique" UNIQUE("email");
ALTER TABLE
    "User" ADD CONSTRAINT "user_theme_check" CHECK ("theme" IN ('light', 'dark'));
CREATE TABLE "Skill"(
    "id" bigserial NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "Skill" ADD PRIMARY KEY("id");
ALTER TABLE
    "Skill" ADD CONSTRAINT "skill_name_unique" UNIQUE("name");
CREATE TABLE "UserSkill"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "skill_id" BIGINT NOT NULL,
    "level" VARCHAR(20) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "UserSkill" ADD CONSTRAINT "userskill_user_id_skill_id_unique" UNIQUE("user_id", "skill_id");
ALTER TABLE
    "UserSkill" ADD PRIMARY KEY("id");
CREATE TABLE "Project"(
    "id" bigserial NOT NULL,
    "owner_id" BIGINT NOT NULL,
    "field_id" BIGINT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL,
    "idea" TEXT NOT NULL,
    "benefits" TEXT NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'open',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "Project" ADD PRIMARY KEY("id");
CREATE INDEX "project_owner_id_index" ON
    "Project"("owner_id");
CREATE INDEX "project_field_id_index" ON
    "Project"("field_id");
CREATE TABLE "ProjectRole"(
    "id" bigserial NOT NULL,
    "project_id" BIGINT NOT NULL,
    "specialization_id" BIGINT NOT NULL,
    "description" TEXT NOT NULL,
    "capacity" SMALLINT NOT NULL,
    "is_open" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "ProjectRole" ADD PRIMARY KEY("id");
ALTER TABLE
    "ProjectRole" ADD CONSTRAINT "projectrole_capacity_check" CHECK ("capacity" >= 1);
CREATE INDEX "projectrole_project_id_index" ON
    "ProjectRole"("project_id");
CREATE TABLE "RoleInterest"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "project_role_id" BIGINT NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "message" TEXT NOT NULL,
    "reviewed_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_user_id_project_role_id_unique" UNIQUE("user_id", "project_role_id");
ALTER TABLE
    "RoleInterest" ADD PRIMARY KEY("id");
CREATE INDEX "roleinterest_project_role_id_index" ON
    "RoleInterest"("project_role_id");
CREATE TABLE "ProjectMembership"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "project_role_id" BIGINT NOT NULL,
    "accepted_interest_id" BIGINT NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "joined_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ended_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_user_id_project_role_id_unique" UNIQUE("user_id", "project_role_id");
ALTER TABLE
    "ProjectMembership" ADD PRIMARY KEY("id");
CREATE INDEX "projectmembership_project_role_id_index" ON
    "ProjectMembership"("project_role_id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_accepted_interest_id_unique" UNIQUE("accepted_interest_id");
CREATE TABLE "PortfolioWork"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL,
    "technologies" TEXT NOT NULL,
    "link" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "PortfolioWork" ADD PRIMARY KEY("id");
CREATE TABLE "Notification"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "type" VARCHAR(255) NOT NULL,
    "payload" jsonb NOT NULL DEFAULT '{}'::jsonb,
    "is_read" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "Notification" ADD PRIMARY KEY("id");
CREATE INDEX "notification_user_id_index" ON
    "Notification"("user_id");
CREATE TABLE "FavoriteProject"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "project_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "FavoriteProject" ADD CONSTRAINT "favoriteproject_user_id_project_id_unique" UNIQUE("user_id", "project_id");
ALTER TABLE
    "FavoriteProject" ADD PRIMARY KEY("id");
CREATE TABLE "FavoriteCandidate"(
    "id" bigserial NOT NULL,
    "owner_id" BIGINT NOT NULL,
    "candidate_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "FavoriteCandidate" ADD CONSTRAINT "favoritecandidate_owner_id_candidate_id_unique" UNIQUE("owner_id", "candidate_id");
ALTER TABLE
    "FavoriteCandidate" ADD PRIMARY KEY("id");
ALTER TABLE
    "Specialization" ADD CONSTRAINT "specialization_field_id_foreign" FOREIGN KEY("field_id") REFERENCES "Field"("id");
ALTER TABLE
    "Notification" ADD CONSTRAINT "notification_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_project_role_id_foreign" FOREIGN KEY("project_role_id") REFERENCES "ProjectRole"("id");
ALTER TABLE
    "Project" ADD CONSTRAINT "project_owner_id_foreign" FOREIGN KEY("owner_id") REFERENCES "User"("id");
ALTER TABLE
    "FavoriteCandidate" ADD CONSTRAINT "favoritecandidate_owner_id_foreign" FOREIGN KEY("owner_id") REFERENCES "User"("id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_project_role_id_foreign" FOREIGN KEY("project_role_id") REFERENCES "ProjectRole"("id");
ALTER TABLE
    "UserSkill" ADD CONSTRAINT "userskill_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "FavoriteProject" ADD CONSTRAINT "favoriteproject_project_id_foreign" FOREIGN KEY("project_id") REFERENCES "Project"("id");
ALTER TABLE
    "Project" ADD CONSTRAINT "project_field_id_foreign" FOREIGN KEY("field_id") REFERENCES "Field"("id");
ALTER TABLE
    "FavoriteCandidate" ADD CONSTRAINT "favoritecandidate_candidate_id_foreign" FOREIGN KEY("candidate_id") REFERENCES "User"("id");
ALTER TABLE
    "User" ADD CONSTRAINT "user_specialization_id_foreign" FOREIGN KEY("specialization_id") REFERENCES "Specialization"("id");
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "FavoriteProject" ADD CONSTRAINT "favoriteproject_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "ProjectRole" ADD CONSTRAINT "projectrole_specialization_id_foreign" FOREIGN KEY("specialization_id") REFERENCES "Specialization"("id");
ALTER TABLE
    "ProjectRole" ADD CONSTRAINT "projectrole_project_id_foreign" FOREIGN KEY("project_id") REFERENCES "Project"("id");
ALTER TABLE
    "UserSkill" ADD CONSTRAINT "userskill_skill_id_foreign" FOREIGN KEY("skill_id") REFERENCES "Skill"("id");
ALTER TABLE
    "PortfolioWork" ADD CONSTRAINT "portfoliowork_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_accepted_interest_id_foreign" FOREIGN KEY("accepted_interest_id") REFERENCES "RoleInterest"("id");