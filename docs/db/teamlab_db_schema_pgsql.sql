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
    "bio" TEXT NULL,
    "account_type" VARCHAR(20) NOT NULL,
    "specialization_id" BIGINT NULL,
    "level" VARCHAR(20) NULL,
    "workload_hours_per_week" SMALLINT NULL,
    "work_format" VARCHAR(20) NULL,
    "employment_type" VARCHAR(20) NULL,
    "search_status" VARCHAR(30) NULL,
    "profile_visibility" VARCHAR(20) NOT NULL DEFAULT 'public',
    "notifications_enabled" BOOLEAN NOT NULL DEFAULT TRUE,
    "city" VARCHAR(255) NULL,
    "avatar" VARCHAR(255) NULL,
    "social_links" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_superuser" BOOLEAN NOT NULL DEFAULT FALSE
);
ALTER TABLE
    "User" ADD PRIMARY KEY("id");
ALTER TABLE
    "User" ADD CONSTRAINT "user_username_unique" UNIQUE("username");
ALTER TABLE
    "User" ADD CONSTRAINT "user_email_unique" UNIQUE("email");
ALTER TABLE
    "User" ADD CONSTRAINT "user_account_type_check" CHECK ("account_type" IN ('participant', 'owner'));
ALTER TABLE
    "User" ADD CONSTRAINT "user_level_check" CHECK ("level" IS NULL OR "level" IN ('junior', 'middle', 'senior'));
ALTER TABLE
    "User" ADD CONSTRAINT "user_work_format_check" CHECK ("work_format" IS NULL OR "work_format" IN ('remote', 'hybrid'));
ALTER TABLE
    "User" ADD CONSTRAINT "user_employment_type_check" CHECK ("employment_type" IS NULL OR "employment_type" IN ('full_time', 'part_time', 'combined'));
ALTER TABLE
    "User" ADD CONSTRAINT "user_search_status_check" CHECK ("search_status" IS NULL OR "search_status" IN ('looking_for_team', 'looking_for_members', 'not_looking'));
ALTER TABLE
    "User" ADD CONSTRAINT "user_profile_visibility_check" CHECK ("profile_visibility" IN ('public', 'matched_only', 'hidden'));
ALTER TABLE
    "User" ADD CONSTRAINT "user_workload_hours_check" CHECK ("workload_hours_per_week" IS NULL OR "workload_hours_per_week" >= 0);
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
ALTER TABLE
    "UserSkill" ADD CONSTRAINT "userskill_level_check" CHECK ("level" IN ('basic', 'middle', 'advanced'));
CREATE TABLE "Project"(
    "id" bigserial NOT NULL,
    "owner_id" BIGINT NOT NULL,
    "field_id" BIGINT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT NOT NULL,
    "problem" TEXT NULL,
    "image" VARCHAR(255) NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'open',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "Project" ADD PRIMARY KEY("id");
ALTER TABLE
    "Project" ADD CONSTRAINT "project_status_check" CHECK ("status" IN ('open', 'closed'));
CREATE INDEX "project_owner_id_index" ON
    "Project"("owner_id");
CREATE INDEX "project_field_id_index" ON
    "Project"("field_id");
CREATE TABLE "ProjectRole"(
    "id" bigserial NOT NULL,
    "project_id" BIGINT NOT NULL,
    "specialization_id" BIGINT NOT NULL,
    "tasks" JSONB NOT NULL DEFAULT '[]',
    "benefits" JSONB NOT NULL DEFAULT '[]',
    "is_open" BOOLEAN NOT NULL DEFAULT TRUE,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "ProjectRole" ADD PRIMARY KEY("id");
CREATE INDEX "projectrole_project_id_index" ON
    "ProjectRole"("project_id");
CREATE TABLE "ProjectRoleSkill"(
    "id" bigserial NOT NULL,
    "project_role_id" BIGINT NOT NULL,
    "skill_id" BIGINT NOT NULL,
    "description" TEXT NOT NULL,
    "order" SMALLINT NOT NULL DEFAULT 1
);
ALTER TABLE
    "ProjectRoleSkill" ADD PRIMARY KEY("id");
ALTER TABLE
    "ProjectRoleSkill" ADD CONSTRAINT "projectroleskill_project_role_id_skill_id_unique" UNIQUE("project_role_id", "skill_id");
ALTER TABLE
    "ProjectRoleSkill" ADD CONSTRAINT "projectroleskill_project_role_id_order_unique" UNIQUE("project_role_id", "order");
CREATE INDEX "projectroleskill_project_role_id_order_index" ON
    "ProjectRoleSkill"("project_role_id", "order");
CREATE INDEX "projectroleskill_skill_id_index" ON
    "ProjectRoleSkill"("skill_id");
CREATE TABLE "RoleInterest"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "project_role_id" BIGINT NOT NULL,
    "source" VARCHAR(20) NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "reviewed_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_user_id_project_role_id_unique" UNIQUE("user_id", "project_role_id");
ALTER TABLE
    "RoleInterest" ADD PRIMARY KEY("id");
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_source_check" CHECK ("source" IN ('application', 'invitation'));
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_status_check" CHECK ("status" IN ('pending', 'accepted', 'rejected'));
CREATE INDEX "roleinterest_project_role_id_index" ON
    "RoleInterest"("project_role_id");
CREATE TABLE "ProjectMembership"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "project_role_id" BIGINT NOT NULL,
    "role_interest_id" BIGINT NOT NULL,
    "status" VARCHAR(20) NOT NULL DEFAULT 'active',
    "joined_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ended_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "ProjectMembership" ADD PRIMARY KEY("id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_status_check" CHECK ("status" IN ('active', 'left', 'removed'));
CREATE INDEX "projectmembership_project_role_id_index" ON
    "ProjectMembership"("project_role_id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_role_interest_id_unique" UNIQUE("role_interest_id");
CREATE UNIQUE INDEX "projectmembership_active_project_role_unique" ON
    "ProjectMembership"("project_role_id") WHERE "status" = 'active';
CREATE TABLE "PortfolioWork"(
    "id" bigserial NOT NULL,
    "user_id" BIGINT NOT NULL,
    "title" VARCHAR(255) NOT NULL,
    "task" TEXT NULL,
    "solution" TEXT NULL,
    "image" VARCHAR(255) NULL,
    "technologies" jsonb NULL,
    "link" VARCHAR(255) NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE
    "PortfolioWork" ADD PRIMARY KEY("id");
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
ALTER TABLE
    "Specialization" ADD CONSTRAINT "specialization_field_id_foreign" FOREIGN KEY("field_id") REFERENCES "Field"("id");
ALTER TABLE
    "RoleInterest" ADD CONSTRAINT "roleinterest_project_role_id_foreign" FOREIGN KEY("project_role_id") REFERENCES "ProjectRole"("id");
ALTER TABLE
    "Project" ADD CONSTRAINT "project_owner_id_foreign" FOREIGN KEY("owner_id") REFERENCES "User"("id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_project_role_id_foreign" FOREIGN KEY("project_role_id") REFERENCES "ProjectRole"("id");
ALTER TABLE
    "UserSkill" ADD CONSTRAINT "userskill_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "FavoriteProject" ADD CONSTRAINT "favoriteproject_project_id_foreign" FOREIGN KEY("project_id") REFERENCES "Project"("id");
ALTER TABLE
    "Project" ADD CONSTRAINT "project_field_id_foreign" FOREIGN KEY("field_id") REFERENCES "Field"("id");
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
    "ProjectRoleSkill" ADD CONSTRAINT "projectroleskill_project_role_id_foreign" FOREIGN KEY("project_role_id") REFERENCES "ProjectRole"("id") ON DELETE CASCADE;
ALTER TABLE
    "ProjectRoleSkill" ADD CONSTRAINT "projectroleskill_skill_id_foreign" FOREIGN KEY("skill_id") REFERENCES "Skill"("id") ON DELETE RESTRICT;
ALTER TABLE
    "PortfolioWork" ADD CONSTRAINT "portfoliowork_user_id_foreign" FOREIGN KEY("user_id") REFERENCES "User"("id");
ALTER TABLE
    "ProjectMembership" ADD CONSTRAINT "projectmembership_role_interest_id_foreign" FOREIGN KEY("role_interest_id") REFERENCES "RoleInterest"("id");
